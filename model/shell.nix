{ pkgs ? import <nixpkgs> {} }:
(pkgs.buildFHSEnv {
    name = "pipzone";
targetPkgs = pkgs: (with pkgs; [
  python312
  python312Packages.pip
  python312Packages.virtualenv
  unzip

  ]);

  multiPkgs = pkgs: (with pkgs; [
  #stdenv.cc.cc.lib
  #libgccjit
  #clang
  #zlib
  zlib
  libglibutil#
  libglvnd
  libGLU
  libglibutil
  glib
  gcc
  graphviz
  ]
  );
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib/:/run/opengl-driver/lib/";
  #shellHook = ''
  #  export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib.outPath}/lib:$LD_LIBRARY_PATH"
  #'';
  runScript = "bash";
}).env
