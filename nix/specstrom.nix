{ pkgs, enableProfiling ? false }:
(import (fetchTarball
  "https://github.com/quickstrom/specstrom/archive/94905fb79a5346390191596b4860b6b7f4ff3482.tar.gz") {
    inherit pkgs;
  }).specstrom
