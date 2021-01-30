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
git clone -b gh-pages https://${GH_TOKEN}@github.com/${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}.git gh-pages
if [ $? -ne 0 ]; then
  echo "(ERROR) Failed to clone the remote repository from 'https://${GH_TOKEN}@github.com/${CIRCLE_PROJECT_REPONAME}.git'"
  exit 1
fi

cd gh-pages

# clear old files and Ciecle CI configuration not to run it.
# Then, this adds new documentation files which are generaged by Hugo.
rm -fR * ./circleci
cp -r ../docs/public/* ./

# set custom domain for the GitHub Pages of this repository
echo ${GH_CUSTOM_DOMAIN} > CNAME

# commit to remote repository on the gh-pages branch. This ignores fails of git-commit command caused by nothing to change.
git add .
git commit -m "Updates gh-pages because of updating the master branch." | true
git push origin gh-pages
