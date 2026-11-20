FROM maven:3.9-eclipse-temurin-21@sha256:99e61abcff91a9b1333463bd8451fb18495d6eba9250ac66a338b518f8278320 AS build
WORKDIR /build
COPY backend-java/pom.xml .
RUN mvn -B -ntp dependency:go-offline
COPY backend-java/src ./src
RUN mvn -B -ntp package && cp target/echobeats-api-*.jar /app.jar

FROM eclipse-temurin:21-jre-noble@sha256:b4f9d2a0bc273417cf5219b7b832bbf0493ed500b7b57d5001d9f83374659060
WORKDIR /app
COPY --from=build /app.jar ./app.jar
EXPOSE 8001
USER 10001
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
