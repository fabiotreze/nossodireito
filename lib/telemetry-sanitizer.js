"use strict";

const TAGS_TO_DELETE = [
  "ai.location.ip",
  "ai.location.city",
  "ai.location.province",
  "ai.location.country",
  "ai.location.countryRegion",
  "ai.user.id",
  "ai.user.authUserId",
  "ai.session.id",
];

const PROPERTIES_TO_DELETE = [
  "User-Agent",
  "Referer",
  "X-Forwarded-For",
  "client-ip",
];

function sanitizeTelemetryEnvelope(envelope) {
  if (envelope.tags) {
    for (const tag of TAGS_TO_DELETE) {
      delete envelope.tags[tag];
    }
  }

  const baseData = envelope.data && envelope.data.baseData;
  if (baseData) {
    if (typeof baseData.url === "string") {
      baseData.url = baseData.url.split("?")[0];
    }
    if (baseData.properties) {
      for (const property of PROPERTIES_TO_DELETE) {
        delete baseData.properties[property];
      }
    }
  }

  return true;
}

module.exports = { sanitizeTelemetryEnvelope };