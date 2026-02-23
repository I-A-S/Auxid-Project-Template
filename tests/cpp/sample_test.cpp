#include <auxid/utils/test.hpp>

using namespace au;

AUT_BEGIN_BLOCK(${AUXID_PROJECT_NAME}, sample)

auto test_ok() -> bool
{
  AUT_CHECK(true);

  return true;
}

auto test_fail() -> bool
{
  AUT_CHECK_EQ(2, 10);

  return true;
}

AUT_BEGIN_TEST_LIST()
AUT_ADD_TEST(test_ok);
AUT_ADD_TEST(test_fail);
AUT_END_TEST_LIST()

AUT_END_BLOCK()

AUT_REGISTER_ENTRY(${AUXID_PROJECT_NAME}, sample);
