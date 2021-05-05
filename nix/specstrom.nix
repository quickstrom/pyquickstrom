{ pkgs, enableProfiling ? false }:
(import (fetchTarball
  "https://github.com/quickstrom/specstrom/archive/00f5d71a19a8c63529c3fb4a3f13931358b155a3.tar.gz") {
    inherit pkgs;
  }).specstrom
