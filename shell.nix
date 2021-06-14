{ pkgs ? (import ./nix/nixpkgs.nix) }:
let
  specstrom = import ./nix/specstrom.nix;
  appEnv = pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    editablePackageSources = { my-app = ./.; };
  };
  todomvc = builtins.fetchTarball {
    url =
      "https://github.com/tastejs/todomvc/archive/41ba86db92336c11e56d425c5151b7ec2932be9a.tar.gz";
  };

in pkgs.mkShell {
  buildInputs = [
    pkgs.bashInteractive

    appEnv
    pkgs.poetry

    pkgs.geckodriver
    pkgs.chromedriver

    specstrom
  ] ++ pkgs.lib.optional pkgs.stdenv.isLinux [
    pkgs.firefox
    pkgs.chromium
  ] ;
  TODOMVC_DIR = todomvc;
  QUICKSTROM_CLIENT_SIDE_DIRECTORY = import ./client-side { inherit pkgs; };
}
