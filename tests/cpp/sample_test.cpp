import auxid;
import auxid.test;

using namespace au;

namespace
{
  struct SampleBlock final : test::Block
  {
    [[nodiscard]] auto get_name() const -> const char * override
    {
      return "${AUXID_PROJECT_NAME}::sample";
    }

    auto declare_tests() -> void override
    {
      add_test("ok", [this] { return test_ok(); });
      add_test("fail", [this] { return test_fail(); });
    }

    auto test_ok() -> bool
    {
      return check(true, "true");
    }

    auto test_fail() -> bool
    {
      return check_eq(2, 10, "2 == 10");
    }
  };

  const test::AutoRegister<SampleBlock> _registered;
} // namespace
