{ pkgs ? (import ./nix/nixpkgs.nix) }:
let
  specstrom = (import ./nix/specstrom.nix {
    inherit pkgs;
    enableProfiling = false;
  });
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

    pkgs.firefox
    pkgs.geckodriver
    pkgs.chromedriver
    pkgs.chromium

    specstrom
  ];
  TODOMVC_DIR = todomvc;
}
