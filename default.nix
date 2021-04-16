{ pkgs ? (import ./nix/nixpkgs.nix), geckodriver ? pkgs.geckodriver
, firefox ? pkgs.firefox, chromedriver ? pkgs.chromedriver
, chromium ? pkgs.chromium }:
let
  specstrom = (import ./nix/specstrom.nix {
    inherit pkgs;
    enableProfiling = false;
  });
in pkgs.poetry2nix.mkPoetryApplication {
  projectDir = ./.;
  python = pkgs.python38;
  propagatedBuildInputs =
    [ specstrom geckodriver firefox chromedriver chromium ];
}
