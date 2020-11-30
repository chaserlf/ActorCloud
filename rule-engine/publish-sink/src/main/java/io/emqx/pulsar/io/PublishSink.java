package io.emqx.pulsar.io;

import com.google.gson.JsonArray;
import io.emqx.stream.common.JsonParser;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.apache.pulsar.functions.api.Record;
import org.apache.pulsar.io.core.Sink;
import org.apache.pulsar.io.core.SinkContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.stream.Stream;

// 将消息发布到mqtt组件中
public class PublishSink implements Sink<String> {
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private OkHttpClient client;
    private String url;

    private static final Logger logger = LoggerFactory.getLogger(PublishSink.class);

    @Override
    public void open(Map<String, Object> config, SinkContext sinkContext) throws Exception {
        PublishSinkConfig publishSinkConfig = PublishSinkConfig.load(config);

        url = publishSinkConfig.getUrl();
        String username = publishSinkConfig.getUsername();
        String password = publishSinkConfig.getPassword();
        if (url == null) {
            throw new IllegalArgumentException("Required publish url not set.");
        }
        client = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .writeTimeout(10, TimeUnit.SECONDS)
                .addInterceptor(new LoggingInterceptor())
                .authenticator((route, response) -> {
                    String credential = Credentials.basic(username, password);
                    return response.request().newBuilder().header("Authorization", credential).build();
                })
                .build();
        logger.info("Init client success");
    }

    @Override
    public void write(Record<String> record) throws Exception {
        String message = record.getValue();
        logger.info("Receive message: {}", message);
        Map<String, Object> actionMessage = JsonParser.parseMqttMessage(message);
        if (actionMessage != null) {
            //noinspection unchecked
            Map<String, Object> action = (Map<String, Object>) actionMessage.get("action");
            String payload = (String) action.get("json");

            ArrayList<Map<String, Object>> values = (ArrayList<Map<String, Object>>) actionMessage.get("values");
            String temperature = values.stream().filter(o -> !o.get("temperature").equals(null)).findFirst().get().get("temperature").toString();

            payload = payload.replace("${temperature}", temperature);

            logger.info("payload: " + payload);
            post(url, payload, new HttpCallback(record));
        }
    }

    @Override
    public void close() {
        client.dispatcher().executorService().shutdown();
        client.connectionPool().evictAll();
        logger.info("Client resources released");
    }

    private void post(String url, String json, Callback callback) {
        RequestBody body = RequestBody.create(JSON, json);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();
        client.newCall(request).enqueue(callback);
    }

    class HttpCallback implements Callback {
        private final Record record;
        HttpCallback(Record record) {
            this.record = record;
        }

        @Override
        public void onFailure(Call call, IOException e) {
            record.fail();
        }

        @Override
        public void onResponse(Call call, Response response) {
            if (response.isSuccessful()) {
                record.ack();
            } else {
                record.fail();
            }
        }
    }

    private static class LoggingInterceptor implements Interceptor {
        @Override
        public Response intercept(Chain chain) throws IOException {
            long t1 = System.nanoTime();
            Request request = chain.request();
            logger.debug("Sending request {}", request.url());
            Response response = chain.proceed(request);
            long t2 = System.nanoTime();
            logger.debug("Received response for {} in {}ms", request.url(), (t2 - t1) / 1e6d);
            return response;
        }
    }
}
