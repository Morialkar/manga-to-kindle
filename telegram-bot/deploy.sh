echo "Deploying Serverless stack..."
BOT_TOKEN=$1 sls deploy --verbose

URL=`BOT_TOKEN=$1 sls info | awk '$1 == "endpoint:" {print $4}'`
echo "Setting up Telegram Webhook: ${URL}"
curl \
    --request POST \
    --url https://api.telegram.org/bot$1/setWebhook \
    --header 'content-type: application/json' \
    --data "{\"url\": \"${URL}\"}"


