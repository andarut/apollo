#ifndef URL_H
#define URL_H

#include <string>

namespace apl
{

struct Url {
  std::string scheme;
  std::string host;
  std::string port;
  std::string path;
};

Url parseUrl(const std::string& urlStr) {
  Url url;

  auto scheme_end = urlStr.find("://");
  if (scheme_end == std::string::npos)
    throw std::runtime_error("Invalid URL, missing scheme");

  url.scheme = urlStr.substr(0, scheme_end);

  auto host_start = scheme_end + 3;
  auto path_start = urlStr.find('/', host_start);

  if (path_start == std::string::npos) {
    url.host = urlStr.substr(host_start);
    url.path = "/";
  } else {
    url.host = urlStr.substr(host_start, path_start - host_start);
    url.path = urlStr.substr(path_start);
  }

  // Split host and port if present
  auto colon_pos = url.host.find(':');
  if (colon_pos != std::string::npos) {
    url.port = url.host.substr(colon_pos + 1);
    url.host = url.host.substr(0, colon_pos);
  } else {
    // default port
    if (url.scheme == "ws")
      url.port = "80";
    else if (url.scheme == "wss")
      url.port = "443";
    else
      url.port = "80";
  }

  return url;
}

} // namespace apl

#endif // URL_H
