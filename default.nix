{ pkgs ? (import ./nix/nixpkgs.nix), specstrom ? import ./nix/specstrom.nix }:
let
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
        --set PATH ${pkgs.lib.makeBinPath [specstrom pkgs.firefox pkgs.geckodriver pkgs.chromium pkgs.chromedriver]} \
        --add-flags "-I$out/share/ulib"

    '';
  };
in quickstrom-wrapped

