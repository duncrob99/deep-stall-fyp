{
  pkgs ? import <nixpkgs> { },
}:

let
  pythonEnv = pkgs.python311.withPackages (ps: [ ]);
in
with pkgs;

pkgs.mkShell {
  packages = [
    pythonEnv
  ];

  buildInputs = with python311Packages; [
    virtualenv # run virtualenv .
    # requests
    # requests-cache
    # types-requests
    # beautifulsoup4
    # types-beautifulsoup4
    # tqdm
    # types-tqdm
    # lxml
    # rich

    setuptools
    python-lsp-server
    pylsp-mypy
    numpy
    matplotlib
  ];

  NIX_LD_LIBRARY_PATH = lib.makeLibraryPath [
    stdenv.cc.cc
    gtk3
    glib
    nss
  ];

  NIX_LD = lib.fileContents "${stdenv.cc}/nix-support/dynamic-linker";

  shellHook = ''
    # fixes libstdc++ issues and libgl.so issues
    export LD_LIBRARY_PATH=${stdenv.cc.cc.lib}/lib/:/run/opengl-driver/lib/:${pkgs.libGL}/lib/:${pkgs.glib.out}/lib/:${python3Packages.greenlet.out}/lib/
    # fixes xcb issues :
    export QT_PLUGIN_PATH=${qt5.qtbase}/${qt5.qtbase.qtPluginPrefix}
    # export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
    # export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true

    source .venv/bin/activate
  '';
}
