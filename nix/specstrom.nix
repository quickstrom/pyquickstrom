{ pkgs, enableProfiling ? false }:
(import (fetchTarball
  "https://github.com/quickstrom/specstrom/archive/2390c50f0a915e92b7895cc14b781e7f1a870d38.tar.gz") {
    inherit pkgs;
  }).specstrom
