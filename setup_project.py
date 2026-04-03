import sys
import os
import shutil
import subprocess
import re
import stat
from pathlib import Path

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 setup_project.py <project_type> <project_name>")
        sys.exit(1)

    project_type = sys.argv[1]
    project_name = sys.argv[2]
    valid_types = ['executable', 'shared_lib', 'static_lib']

    if project_type not in valid_types:
        print(f"Error: <project_type> must be one of {valid_types}")
        sys.exit(1)

    if not project_name.strip():
        print("Error: <project_name> cannot be empty.")
        sys.exit(1)

    root_dir = Path.cwd()

    readme_path = root_dir / "README.md"
    if readme_path.exists():
        with open(readme_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(first_line)

    if project_type == 'executable':
        root_cmake_path = root_dir / "CMakeLists.txt"
        if root_cmake_path.exists():
            with open(root_cmake_path, 'r', encoding='utf-8') as f:
                root_cmake_content = f.read()

            root_cmake_content = re.sub(
                r'option\(\$\{AUXID_PROJECT_NAME\}_BUILD_TESTS\s+"Build unit tests"\s+\$\{\$\{AUXID_PROJECT_NAME\}_IS_TOP_LEVEL\}\)\n?', 
                '', 
                root_cmake_content
            )
            root_cmake_content = re.sub(
                r'if\(\$\{AUXID_PROJECT_NAME\}_BUILD_TESTS\)\s*add_subdirectory\(tests\)\s*endif\(\)\n?', 
                '', 
                root_cmake_content
            )

            with open(root_cmake_path, 'w', encoding='utf-8') as f:
                f.write(root_cmake_content)

    skip_dirs = {'libauxid'}
    script_path = Path(__file__).resolve()

    for filepath in root_dir.rglob('*'):
        if filepath.is_file():
            if any(part in skip_dirs for part in filepath.parts) or filepath.resolve() == script_path:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "${AUXID_PROJECT_NAME}" in content:
                    new_content = content.replace("${AUXID_PROJECT_NAME}", project_name)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
            except UnicodeDecodeError:
                pass

    src_dir = root_dir / "src"
    src_cpp_dir = src_dir / "cpp"
    src_hpp_dir = src_dir / "hpp"
    src_cmake_path = src_dir / "CMakeLists.txt"
    
    if project_type == 'executable':
        for d in ['include', 'tests']:
            dir_to_remove = root_dir / d
            if dir_to_remove.exists():
                shutil.rmtree(dir_to_remove)
        
        main_cpp = src_cpp_dir / "main.cpp"
        main_cpp.parent.mkdir(parents=True, exist_ok=True)
        with open(main_cpp, 'w', encoding='utf-8') as f:
            f.write(f"#include <pch.hpp>\n\nint main(int argc, char* argv[]) {{\n    printf(\"Hello from {project_name}!\\n\");\n    return 0;\n}}\n")

        pch_hpp = src_hpp_dir / "pch.hpp"
        pch_hpp.parent.mkdir(parents=True, exist_ok=True)
        with open(pch_hpp, 'w', encoding='utf-8') as f:
            f.write(f"#pragma once\n\n#include <auxid/auxid.hpp>\n\n")

        os.remove(src_cpp_dir / ".gitkeep")
        os.remove(src_hpp_dir / ".gitkeep")

        with open(src_cmake_path, 'w', encoding='utf-8') as f:
            f.write(f"add_executable({project_name} cpp/main.cpp)\n\n"
                    f"target_include_directories({project_name} PRIVATE hpp)\n"
                    f"target_link_libraries({project_name} PRIVATE libauxid auxid_platform_standard)\n\n"
                    f"target_precompile_headers({project_name} PRIVATE hpp/pch.hpp)\n"
                )

    else:
        inc_dir = root_dir / "include" / project_name
        inc_dir.mkdir(parents=True, exist_ok=True)
        
        hpp_file = inc_dir / f"{project_name}.hpp"
        with open(hpp_file, 'w', encoding='utf-8') as f:
            f.write(f"#pragma once\n\n#include <auxid/auxid.hpp>\n\nnamespace {project_name} {{\n    // TODO: Add library declarations\n}}\n")
            
        os.remove(src_cpp_dir / ".gitkeep")
        os.remove(root_dir / "include" / ".gitkeep")

        cpp_file = src_cpp_dir / f"{project_name}.cpp"
        cpp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cpp_file, 'w', encoding='utf-8') as f:
            f.write(f"#include <{project_name}/{project_name}.hpp>\n\nnamespace {project_name} {{\n    // TODO: Add library implementations\n}}\n")

        lib_type = "SHARED" if project_type == 'shared_lib' else "STATIC"
        with open(src_cmake_path, 'w', encoding='utf-8') as f:
            f.write(f"add_library({project_name} {lib_type} cpp/{project_name}.cpp)\n\n"
                    f"target_include_directories({project_name} PUBLIC\n"
                    f"    $<BUILD_INTERFACE:${{{project_name}_ROOT}}/include>\n"
                    f"    $<INSTALL_INTERFACE:include>\n"
                    f")\n"
                    f"target_include_directories({project_name} PRIVATE hpp)\n\n"
                    f"target_link_libraries({project_name} PUBLIC libauxid)\n"
                    f"target_link_libraries({project_name} PRIVATE auxid_platform_standard)\n")

    print("Setting up fresh Git repository...")
    try:
        git_dir = root_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir, onerror=remove_readonly)
            
        subprocess.run(["git", "init"], check=True)
        
        submodule_url = "https://github.com/I-A-S/Auxid" 
        print(f"Adding libauxid submodule from {submodule_url}...")
        subprocess.run(["git", "submodule", "add", submodule_url, "libauxid"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git operations failed. Error: {e}")
    except Exception as e:
        print(f"Warning: Unexpected error during Git setup: {e}")

    try:
        os.remove(script_path)
        print(f"Success! Scaffolded {project_name} as a {project_type}.")
    except Exception as e:
        print(f"Project set up, but failed to delete setup script: {e}")

if __name__ == "__main__":
    main()
