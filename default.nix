{ pkgs ? (import ./nix/nixpkgs.nix), geckodriver ? pkgs.geckodriver
, firefox ? pkgs.firefox, chromedriver ? pkgs.chromedriver
, chromium ? pkgs.chromium }:
let
  specstrom = import ./nix/specstrom.nix;
  poetry2nix = import ./nix/poetry2nix.nix { inherit pkgs; };

  quickstrom = poetry2nix.mkPoetryApplication {
    projectDir = ./.;
    python = pkgs.python38;
    propagatedBuildInputs = [ specstrom ];
    checkInputs = [ pkgs.nodePackages.pyright ];
    checkPhase = ''
      pyright -p . quickstrom tests
      pytest
    '';

  };

  client-side = import ./client-side { inherit pkgs; };
  html-report = import ./html-report { inherit pkgs; };

  quickstrom-wrapped = pkgs.symlinkJoin {
    name = "quickstrom";
    paths = [ quickstrom ];
    buildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      mkdir -p $out/share
      cp -r ${./ulib} $out/share/ulib
      wrapProgram $out/bin/quickstrom \
        --set QUICKSTROM_CLIENT_SIDE_DIRECTORY ${client-side} \
        --set QUICKSTROM_HTML_REPORT_DIRECTORY ${html-report} \
        --add-flags "-I$out/share/ulib"

    '';
  };
in quickstrom-wrapped

