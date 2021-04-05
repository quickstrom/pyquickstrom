{ pkgs ? import <nixpkgs> { } }:

let

  # specstrom = (import (fetchTarball
  #   "https://github.com/quickstrom/specstrom/archive/15cc4c145319d9770e797e9b1afa8ac10a73fa85.tar.gz")
  #   { inherit pkgs; }).specstrom;
  specstrom = pkgs.haskell.lib.enableExecutableProfiling (import ../../specstrom { inherit pkgs; }).specstrom;

  wd-chrome = pkgs.writeShellScriptBin "quickstrom-wd-chrome" ''
    docker run --rm -d \
      --name webdriver-chrome \
      --network=host \
      -v /dev/shm:/dev/shm \
      -v /tmp:/tmp \
      selenium/standalone-chrome:3.141.59-20200826
  '';

in pkgs.mkShell {
  buildInputs = [
    # keep this line if you use bash
    pkgs.bashInteractive
    pkgs.python38
    pkgs.poetry
    pkgs.geckodriver
    pkgs.chromedriver

    wd-chrome
    specstrom
  ];
}
