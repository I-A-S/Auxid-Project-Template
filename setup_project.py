import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path


VALID_TYPES = [
    "executable",
    "shared_lib",
    "static_lib",
    "legacy_executable",
    "legacy_shared_lib",
    "legacy_static_lib",
]


def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def remove_directory(path):
    if path.exists():
        shutil.rmtree(path)


def trim_template_readme(root_dir):
    readme_path = root_dir / "README.md"
    if not readme_path.exists():
        return

    with readme_path.open("r", encoding="utf-8") as readme:
        first_line = readme.readline()
    write_text(readme_path, first_line)


def remove_test_configuration(root_dir):
    root_cmake_path = root_dir / "CMakeLists.txt"
    if not root_cmake_path.exists():
        return

    root_cmake_content = root_cmake_path.read_text(encoding="utf-8")
    root_cmake_content = re.sub(
        r'option\(\$\{AUXID_PROJECT_NAME\}_BUILD_TESTS\s+"Build unit tests"\s+\$\{\$\{AUXID_PROJECT_NAME\}_IS_TOP_LEVEL\}\)\n?',
        "",
        root_cmake_content,
    )
    root_cmake_content = re.sub(
        r'if\(\$\{AUXID_PROJECT_NAME\}_BUILD_TESTS\)\s*add_subdirectory\(tests\)\s*endif\(\)\n?',
        "",
        root_cmake_content,
    )
    write_text(root_cmake_path, root_cmake_content)


def replace_project_name(root_dir, project_name, script_path):
    for filepath in root_dir.rglob("*"):
        if not filepath.is_file():
            continue
        if "libauxid" in filepath.parts or filepath.resolve() == script_path:
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if "${AUXID_PROJECT_NAME}" in content:
            write_text(filepath, content.replace("${AUXID_PROJECT_NAME}", project_name))


def module_interface(project_name):
    return (
        f"export module {project_name};\n\n"
        "export import auxid;\n\n"
        f"export namespace {project_name}\n"
        "{\n"
        "  // TODO: Add module declarations\n"
        "}\n"
    )


def executable_main(project_name, module_based):
    imported_module = project_name if module_based else "auxid"
    return (
        "#include <iostream>\n\n"
        f"import {imported_module};\n\n"
        "using namespace au;\n\n"
        "auto main() -> int\n"
        "{\n"
        "    auxid::MainThreadGuard _main_thread_guard;\n"
        f'    std::cout << "Hello from {project_name}!\\n";\n'
        "    return 0;\n"
        "}\n"
    )


def configure_executable(root_dir, project_name, module_based):
    src_dir = root_dir / "src"
    src_cpp_dir = src_dir / "cpp"
    src_hpp_dir = src_dir / "hpp"

    remove_directory(root_dir / "include")
    remove_directory(root_dir / "tests")
    remove_directory(src_hpp_dir)

    (src_cpp_dir / ".gitkeep").unlink(missing_ok=True)
    write_text(
        src_cpp_dir / "main.cpp",
        executable_main(project_name, module_based),
    )

    if module_based:
        write_text(
            src_dir / "modules" / f"{project_name}.cppm",
            module_interface(project_name),
        )
        cmake_content = (
            f"add_executable({project_name} cpp/main.cpp)\n\n"
            f"target_sources({project_name}\n"
            "    PRIVATE FILE_SET project_modules TYPE CXX_MODULES\n"
            '        BASE_DIRS "${CMAKE_CURRENT_LIST_DIR}/modules"\n'
            "        FILES\n"
            f"            modules/{project_name}.cppm\n"
            ")\n\n"
            f"target_link_libraries({project_name} PRIVATE libauxid)\n"
            f"set_target_properties({project_name} PROPERTIES CXX_SCAN_FOR_MODULES ON)\n"
        )
    else:
        cmake_content = (
            f"add_executable({project_name} cpp/main.cpp)\n\n"
            f"target_link_libraries({project_name} PRIVATE libauxid)\n"
            f"set_target_properties({project_name} PROPERTIES CXX_SCAN_FOR_MODULES ON)\n"
        )

    write_text(src_dir / "CMakeLists.txt", cmake_content)


def add_library_test_import(root_dir, project_name, module_based):
    sample_test_path = root_dir / "tests" / "cpp" / "sample_test.cpp"
    if not sample_test_path.exists():
        return

    content = sample_test_path.read_text(encoding="utf-8")
    if module_based:
        content = content.replace(
            "import auxid.test;\n",
            f"import auxid.test;\nimport {project_name};\n",
            1,
        )
    else:
        content = f"#include <{project_name}/{project_name}.hpp>\n\n" + content
    write_text(sample_test_path, content)


def configure_library(root_dir, project_type, project_name, module_based):
    src_dir = root_dir / "src"
    src_cpp_dir = src_dir / "cpp"
    (src_cpp_dir / ".gitkeep").unlink(missing_ok=True)

    lib_type = "SHARED" if project_type.endswith("shared_lib") else "STATIC"

    if module_based:
        remove_directory(root_dir / "include")
        write_text(
            src_dir / "modules" / f"{project_name}.cppm",
            module_interface(project_name),
        )
        write_text(
            src_cpp_dir / f"{project_name}.cpp",
            f"module {project_name};\n\n"
            f"namespace {project_name}\n"
            "{\n"
            "  // TODO: Add module implementations\n"
            "}\n",
        )
        cmake_content = (
            f"add_library({project_name} {lib_type}\n"
            f"    cpp/{project_name}.cpp\n"
            ")\n\n"
            f"target_sources({project_name}\n"
            "    PUBLIC FILE_SET project_modules TYPE CXX_MODULES\n"
            '        BASE_DIRS "${CMAKE_CURRENT_LIST_DIR}/modules"\n'
            "        FILES\n"
            f"            modules/{project_name}.cppm\n"
            ")\n\n"
            f"target_link_libraries({project_name} PUBLIC libauxid)\n"
            f"set_target_properties({project_name} PROPERTIES CXX_SCAN_FOR_MODULES ON)\n"
        )
    else:
        inc_dir = root_dir / "include" / project_name
        (root_dir / "include" / ".gitkeep").unlink(missing_ok=True)
        write_text(
            inc_dir / f"{project_name}.hpp",
            "#pragma once\n\n"
            f"namespace {project_name} {{\n"
            "    // TODO: Add library declarations\n"
            "}\n",
        )
        write_text(
            src_cpp_dir / f"{project_name}.cpp",
            f"#include <{project_name}/{project_name}.hpp>\n\n"
            "import auxid;\n\n"
            f"namespace {project_name} {{\n"
            "    // TODO: Add library implementations\n"
            "}\n",
        )
        cmake_content = (
            f"add_library({project_name} {lib_type} cpp/{project_name}.cpp)\n\n"
            f"target_include_directories({project_name} PUBLIC\n"
            f"    $<BUILD_INTERFACE:${{{project_name}_ROOT}}/include>\n"
            "    $<INSTALL_INTERFACE:include>\n"
            ")\n\n"
            f"target_link_libraries({project_name} PUBLIC libauxid)\n"
            f"set_target_properties({project_name} PROPERTIES CXX_SCAN_FOR_MODULES ON)\n"
        )

    write_text(src_dir / "CMakeLists.txt", cmake_content)
    add_library_test_import(root_dir, project_name, module_based)


def scaffold_project(root_dir, project_type, project_name, script_path=None):
    """Generate project files without performing Git operations."""
    script_path = (script_path or Path(__file__)).resolve()
    is_executable = project_type.endswith("executable")
    module_based = not project_type.startswith("legacy_")

    trim_template_readme(root_dir)
    if is_executable:
        remove_test_configuration(root_dir)
    replace_project_name(root_dir, project_name, script_path)

    if is_executable:
        configure_executable(root_dir, project_name, module_based)
    else:
        configure_library(root_dir, project_type, project_name, module_based)


def initialize_git_repository(root_dir):
    print("Setting up fresh Git repository...")
    try:
        git_dir = root_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir, onerror=remove_readonly)

        subprocess.run(["git", "init"], check=True)

        submodule_url = "https://github.com/I-A-S/Auxid"
        print(f"Adding libauxid submodule from {submodule_url}...")
        subprocess.run(
            ["git", "submodule", "add", submodule_url, "libauxid"],
            check=True,
        )
    except subprocess.CalledProcessError as error:
        print(f"Warning: Git operations failed. Error: {error}")
    except Exception as error:
        print(f"Warning: Unexpected error during Git setup: {error}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 setup_project.py <project_type> <project_name>")
        sys.exit(1)

    project_type = sys.argv[1]
    project_name = sys.argv[2]

    if project_type not in VALID_TYPES:
        print(f"Error: <project_type> must be one of {VALID_TYPES}")
        sys.exit(1)

    if not project_name.strip():
        print("Error: <project_name> cannot be empty.")
        sys.exit(1)

    root_dir = Path.cwd()
    script_path = Path(__file__).resolve()

    scaffold_project(root_dir, project_type, project_name, script_path)
    initialize_git_repository(root_dir)

    try:
        os.remove(script_path)
        print(f"Success! Scaffolded {project_name} as a {project_type}.")
    except Exception as error:
        print(f"Project set up, but failed to delete setup script: {error}")


if __name__ == "__main__":
    main()
