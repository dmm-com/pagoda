#!/bin/sh

#
# This script is mainly used by CI to update contents of gh-pages to the latest one.
#
set -e

if [ -z "${GH_TOKEN}" ]; then
  echo '(ERROR) The environment variables "GH_TOKEN" have to be set'
  exit 1
fi

# ${GH_TOKEN} is an access token of GitHub to update GitHub pages of the repository
git clone -b gh-pages https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git gh-pages
if [ $? -ne 0 ]; then
  echo "(ERROR) Failed to clone the remote repository from 'https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git'"
  exit 1
fi

cd gh-pages

# clear old files and Ciecle CI configuration not to run it.
# Then, this adds new documentation files which are generaged by Hugo.
rm -fR * ./circleci
cp -r ../docs/public/* ./

# commit to remote repository on the gh-pages branch
git add .
git commit -m "Updates gh-pages because of updating the master branch."
git push origin gh-pages
