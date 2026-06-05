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

const BASE_DATA_FIELDS_TO_DELETE = [
  "client_IP",
  "client_City",
  "client_CountryOrRegion",
  "user_Id",
  "session_Id",
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
    for (const field of BASE_DATA_FIELDS_TO_DELETE) {
      delete baseData[field];
    }
    if (baseData.properties) {
      for (const property of PROPERTIES_TO_DELETE) {
        delete baseData.properties[property];
      }
      for (const field of BASE_DATA_FIELDS_TO_DELETE) {
        delete baseData.properties[field];
      }
    }
  }

  return true;
}

module.exports = { sanitizeTelemetryEnvelope };