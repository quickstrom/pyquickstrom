{ pkgs ? (import ./nix/nixpkgs.nix), geckodriver ? pkgs.geckodriver
, firefox ? pkgs.firefox, chromedriver ? pkgs.chromedriver
, chromium ? pkgs.chromium }:
let
  specstrom = import ./nix/specstrom.nix;

  quickstrom = pkgs.poetry2nix.mkPoetryApplication {
    projectDir = ./.;
    python = pkgs.python38;
    propagatedBuildInputs =
      [ specstrom geckodriver firefox chromedriver chromium ];
    checkInputs = [pkgs.nodePackages.pyright];
    checkPhase = ''
      pyright quickstrom
    '';

  };

  client-side = import ./client-side { inherit pkgs; };

  quickstrom-wrapped = pkgs.symlinkJoin {
    name = "quickstrom";
    paths = [ quickstrom ];
    buildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      mkdir -p $out/share
      cp -r ${./ulib} $out/share/ulib
      wrapProgram $out/bin/quickstrom \
        --set QUICKSTROM_CLIENT_SIDE_DIRECTORY ${client-side} \
        --add-flags "-I$out/share/ulib"

    '';
  };
in quickstrom-wrapped

