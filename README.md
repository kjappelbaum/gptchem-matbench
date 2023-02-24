# gptchem-matbench

Running the gptchem on the matbench tasks.
Since there might be issues with the API sometimes, we serialize the results for each dataset to json and then build the `MatbenchBenchmark` with all the results.