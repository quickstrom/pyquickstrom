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
in pkgs.mkShell {
  buildInputs = [
    pkgs.bashInteractive

    appEnv

    pkgs.geckodriver
    pkgs.firefox

    specstrom
  ];
}
