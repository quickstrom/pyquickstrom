{ pkgs }:
pkgs.callPackage (fetchTarball "https://github.com/nix-community/poetry2nix/archive/705cbfa10e3d9bfed2e59e0256844ae3704dbd7e.tar.gz") { inherit pkgs; }