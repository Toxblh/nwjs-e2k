// minimal N-API addon for the e2k Electron/NW.js smoke test
#include <node_api.h>
static napi_value Hello(napi_env env, napi_callback_info) {
  napi_value s; napi_create_string_utf8(env, "hello from an e2k native addon", NAPI_AUTO_LENGTH, &s); return s;
}
static napi_value Add(napi_env env, napi_callback_info info) {
  size_t argc = 2; napi_value argv[2]; napi_get_cb_info(env, info, &argc, argv, nullptr, nullptr);
  double a = 0, b = 0; napi_get_value_double(env, argv[0], &a); napi_get_value_double(env, argv[1], &b);
  napi_value r; napi_create_double(env, a + b, &r); return r;
}
static napi_value Init(napi_env env, napi_value exports) {
  napi_property_descriptor d[] = { {"hello", 0, Hello, 0, 0, 0, napi_default, 0}, {"add", 0, Add, 0, 0, 0, napi_default, 0} };
  napi_define_properties(env, exports, 2, d); return exports;
}
NAPI_MODULE(NODE_GYP_MODULE_NAME, Init)
