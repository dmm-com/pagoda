#!/bin/sh

# these environment variable must be given from outside (e.g. from Circle CI)
# $GIST_USER: gist username to post entire coverage
# $GIST_TOKEN: gist api token for $GIST_USER
# $GIST_ENDPOINT: gist api endpoint
# $SLACK_ENDPOINT: slack endpoint to post summary

# run coverage
coverage report > coverage.txt

# all
GIST_DESCRIPTION=coverage-$CIRCLE_PROJECT_USERNAME-$CIRCLE_PROJECT_REPONAME-$CIRCLE_BUILD_NUM
GIST_FILENAME=$GIST_DESCRIPTION.txt

echo '{
  "public":"true",
  "desctiption":"'$GIST_DESCRIPTION'",
  "files": {
    "'$GIST_FILENAME'" :{
       "content": "' > coverage.json
echo 'build '$CIRCLE_BUILD_URL'\\n' >> coverage.json
echo 'git   '$CIRCLE_COMPARE_URL'\\n' >> coverage.json
echo '\\n' >> coverage.json
sed -e 's/$/\\n/g' coverage.txt >> coverage.json
echo '"
    }
  }
}' >> coverage.json

curl --user "$GIST_USER:$GIST_TOKEN" -X POST --data @coverage.json $GIST_ENDPOINT > response.json

GIST_URL=$(grep 'html_url' response.json | grep 'gist' | sed -e 's/.*: //g;s/[",]//g')

rm coverage.json
rm response.json

# sumamry
echo "#$CIRCLE_BUILD_NUM" > coverage-summary.txt
echo "build : $CIRCLE_BUILD_URL" >> coverage-summary.txt
echo "git   : $CIRCLE_COMPARE_URL" >> coverage-summary.txt
echo "" >> coverage-summary.txt
head -n 1 coverage.txt >> coverage-summary.txt
tail -n 1 coverage.txt >> coverage-summary.txt
echo "detail: $GIST_URL" >> coverage-summary.txt

echo '{"text":"```' > coverage-summary.json
cat coverage-summary.txt >> coverage-summary.json
echo '```"}' >> coverage-summary.json

curl -s -S -H 'Content-type: application/json' -X POST --data "$(cat coverage-summary.json)" $SLACK_ENDPOINT

rm coverage-summary.txt
rm coverage-summary.json
rm coverage.txt
