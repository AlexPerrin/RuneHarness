# The server image of one tree T: upstream's release bundle (release-server.yml: server.jar, game.yml, .data/ without
# raw-cache), run as its release notes say, `java -jar server.jar` in that directory; no key. `up` runs it with a key
# generated for the change; `deploy` layers the live key on top (hash-checked, never printed) for the test server.
# Build context: the build copy's staged bundle. Ports as update-test-server.yml: 43594 game, 9091 Central link, 9090 http.
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --chown=1000:1000 . /app/
USER 1000
ENV JAVA_OPTS=-Xmx2g
EXPOSE 43594 9091 9090
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar server.jar"]
