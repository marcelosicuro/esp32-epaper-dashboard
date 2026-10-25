#pragma once
#include <cstdio>
#include <string>

// GET via curl (o http_request nativo do ESPHome não compila no macOS).
// status = 0 quando a conexão falha.
inline std::string sim_http_get(const std::string &url, int *status) {
  std::string cmd = "curl -s -m 15 -w '\\n%{http_code}' '" + url + "' 2>/dev/null";
  std::string out;
  *status = 0;
  FILE *p = popen(cmd.c_str(), "r");
  if (!p) return out;
  char buf[1024];
  size_t n;
  while ((n = fread(buf, 1, sizeof(buf), p)) > 0) out.append(buf, n);
  pclose(p);
  size_t nl = out.rfind('\n');
  if (nl == std::string::npos) return "";
  *status = atoi(out.c_str() + nl + 1);
  if (*status == 0 && url.rfind("file://", 0) == 0 && nl > 0) *status = 200;  // curl não informa status em file://
  out.resize(nl);
  return out;
}
