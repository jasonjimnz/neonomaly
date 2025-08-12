
class CypherQueriesEnum:
    CREATE_SERVICE_QUERY: str = """
    MATCH (u:User {id: $user_id})
    CREATE (s:Service {
        id: $id,
        name: $name,
        description: $description,
        created_at: $created_at
    })<-[:OWNS]-(u)
    RETURN s
    """

    LIST_SERVICES_QUERY: str = """
    MATCH (u:User {id: $user_id})-[:OWNS]->(s:Service)
    RETURN s
    ORDER BY s.created_at DESC
    """

    GET_SERVICE_QUERY: str = """
    MATCH (u:User {id: $user_id})-[:OWNS]->(s:Service {id: $service_id})
    RETURN s
    """

    CHECK_EXISTING_METRIC: str = """
    MATCH (s:Service {id: $service_id})-[:MONITORS]->(m:Metric {name: $name})
    RETURN m
    """

    CREATE_METRIC_QUERY: str = """
    MATCH (s:Service {id: $service_id})
    CREATE (m:Metric {
        id: $id,
        name: $name,
        description: $description
    })<-[:MONITORS]-(s)
    RETURN m
    """

    GET_METRICS_FROM_SERVICE_QUERY: str = """
    MATCH (s:Service {id: $service_id})-[:MONITORS]->(m:Metric)
    OPTIONAL MATCH (m)-[:LATEST_READING]->(r:MetricReading)
    RETURN m, r
    """

    GET_METRIC_READING_SERVICE_QUERY: str = """
    MATCH (u:User {id: $user_id})-[:OWNS]->(s:Service)-[:MONITORS]->(m:Metric {id: $metric_id})
    RETURN m, s.id AS service_id
    """

    CREATE_METRIC_READING_QUERY: str = """
    MATCH (s:Service {id: $service_id})-[:MONITORS]->(m:Metric {id: $metric_id})
    WITH s, m, $metric_value AS metricValue, $timestamp AS now
    OPTIONAL MATCH (m)-[r:LATEST_READING]->(oldReading:MetricReading)
    DELETE r
    CREATE (newReading:MetricReading {id: $reading_id, value: metricValue, timestamp: now})
    CREATE (m)-[:LATEST_READING]->(newReading)
    WITH oldReading, newReading
    WHERE oldReading IS NOT NULL
    CREATE (oldReading)-[:NEXT]->(newReading)

    RETURN newReading.timestamp AS ingestedTimestamp
    """

    CHECK_ANOMALY_DETECTION: str = """
    // 1. Find the latest reading for the specified metric
    MATCH (s:Service {id: $service_id})-[:MONITORS]->(m:Metric {name: $metric_name})-[:LATEST_READING]->(latestReading)
    // 2. Define the start time for our window
    WITH s, m, latestReading, $time_window_seconds AS timeWindowSeconds, $sigma_threshold AS sigmaThreshold, 
         (latestReading.timestamp - ($time_window_seconds * 1000)) AS windowStartTimestamp
    // 3. Traverse backwards through the linked list to find all readings within the window
    MATCH (latestReading)<-[:NEXT*0..]-(reading:MetricReading)
    WHERE reading.timestamp >= windowStartTimestamp
    // 4. Calculate the mean and standard deviation for the window
    WITH latestReading, sigmaThreshold, avg(reading.value) AS mean, stdev(reading.value) AS stdDev
    // 5. Check if the latest value is an anomaly and return the results
    WITH latestReading, mean, stdDev,
         (abs(latestReading.value - mean) > (sigmaThreshold * stdDev)) AS isAnomaly
    RETURN
      latestReading.timestamp AS timestamp,
      latestReading.value AS value,
      round(mean, 2) AS windowMean,
      round(stdDev, 2) AS windowStdDev,
      isAnomaly
    """