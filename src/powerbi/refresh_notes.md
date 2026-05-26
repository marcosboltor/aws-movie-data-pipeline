# Power BI Refresh Notes

Power BI Desktop connects to Amazon Athena through the generic ODBC connector using the Amazon Athena ODBC driver.

In the current implementation, the dashboard can be refreshed manually from Power BI Desktop by using the `Refresh` option.

For a production environment, the report can be published to Power BI Service and refreshed on a schedule using Power BI Gateway. The scheduled refresh should be aligned with the pipeline execution, for example on Mondays and Fridays at 09:00, after the Bronze, Silver and Gold layers have been updated.
