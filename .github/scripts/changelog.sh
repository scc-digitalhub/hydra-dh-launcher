#!/bin/bash

if [ "$2" = "true" ]; then
  touch CHANGELOG.md
else
  git-cliff --unreleased --tag ${1}  -c .github/scripts/cliff.toml -v -o
fi
