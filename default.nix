{ pkgs ? import <nixpkgs> { } }:

let

  # specstrom = (import (fetchTarball
  #   "https://github.com/quickstrom/specstrom/archive/15cc4c145319d9770e797e9b1afa8ac10a73fa85.tar.gz")
  #   { inherit pkgs; }).specstrom;
  specstrom = (import ../../specstrom {
    inherit pkgs;
    enableProfiling = true;
  }).specstrom;
in pkgs.poetry2nix.mkPoetryApplication { 
  projectDir = ./.;
  python = pkgs.python38;
  propagatedBuildInputs = [
    specstrom
    pkgs.geckodriver
    pkgs.firefox
    pkgs.chromedriver
    pkgs.chromium
  ];
}
