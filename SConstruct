import os
import excons

version = "2.3.4"

env = excons.MakeBaseEnv()

instfiles = {"maya/python": ["python/studiolibrary"],
             "maya/python/studiolibrary": ["resource", "examples"] + excons.glob("*.md"),
             "maya/scripts": excons.glob("scripts/*"),
             "maya/icons": excons.glob("icons/*"),
             "maya/shelves": excons.glob("shelves/*")}

prjs = [
  { "name": "StudioLibrary",
    "type": "install",
    "install": instfiles
  }
]

excons.DeclareTargets(env, prjs)

if "eco" in COMMAND_LINE_TARGETS:
  tgtdirs = {"maya/python": "/python",
             "maya/python/studiolibrary": "/python/studiolibrary",
             "maya/scripts": "/scripts",
             "maya/icons": "/icons",
             "maya/shelves": "/shelves"}
  excons.EcosystemDist(env, "StudioLibrary.env", tgtdirs, targets=instfiles, name="StudioLibrary", version=version)
