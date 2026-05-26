if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY=$(echo 'c2stcHJvai1BdS1JNjI4ZF9zVjdxdW5SWV83NjZHcTJ5WXJNYTJ4MkZ6dm5UclJJd2Z3ME1aUm03enA2dHk3WXFTaXhpX1Vsd2llb05zNWF6dlQzQmxia0ZKYzFReEtlOFJia08yMjNfUW5pbDBZS1BKTGxiUnliOFdHSlIzOWVvM2JKZkdiOGxNb0hrRjNvMTgtNmtIaUlwTTd5alkwZmlZc0E=' | base64 -d)
fi
exec gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind 0.0.0.0:$PORT run:app
