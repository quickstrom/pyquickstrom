{ pkgs ? (import ./nix/nixpkgs.nix) }:
let
  specstrom = (import ./nix/specstrom.nix {
    inherit pkgs;
    enableProfiling = false;
  });
in pkgs.poetry2nix.mkPoetryApplication { 
  projectDir = ./.;
  python = pkgs.python38;
  propagatedBuildInputs = [
    specstrom
    pkgs.geckodriver
    pkgs.firefox
    # pkgs.chromedriver
    # pkgs.chromium
  ];
}
