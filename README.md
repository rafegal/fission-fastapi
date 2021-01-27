# fission-fastapi

It's an environment based in FastAPI to be used with a [fission platform](https://fission.io/). 

Docker hub: https://hub.docker.com/r/rafegal/fission-fastapi  
Last FasAPI version: 0.63.0

To pull: 

```
docker pull rafegal/fission-fastapi:0.63.0
```

To create your fission environment:

```
fission env create --name fastapi --image rafegal/fission-fastapi:0.63.0
```
After you created a fission environment based on this image, you need to create a function in the correct format, for it you need to look at the "function_fastapi.py", it's a perfect example for you to use as a template.

But first you may want to test if your new FastAPI environment is ok, you can use the "test_fastapi.py" function for it. This function is more simple and efficient to test if your environment is ok.

Creating the function test-fastapi
```
fission function create --env <YOUR-FASTAPI-ENV>--name test-fastapi --code test_fastapi.py
```

Testing the function test-fastapi
```
fission function test --name test-fastapi
```

The "test_fastapi.py" function is not a good example of how to mount its function correctly with the FastAPI environment, it is only useful as a test.
Therefore, to use the "function_fastapi.py" function you should follow the steps below:

Creating the function
```
fission function create --env <YOUR-FASTAPI-ENV> --url /function-fastapi/  --name function-fastapi --code function_fastapi.py
```

To test you can use the "get" http method, an error of 400 should appear.
For a perfect test you need to follow the documentation of the function, to access it you must access the address below:

```
http://<YOUR-FISSION-HOST>/function-fastapi/?docs_func=1
```
