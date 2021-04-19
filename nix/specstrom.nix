{ pkgs, enableProfiling ? false }:
(import (fetchTarball
  "https://github.com/quickstrom/specstrom/archive/2e65862c6b75bcb13ad2d6e293163cd50085145b.tar.gz") {
    inherit pkgs;
  }).specstrom
