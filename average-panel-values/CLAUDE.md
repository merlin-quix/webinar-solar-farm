## Project Overview

In this project, you are a helpful assistant that is designed to create runnable python programs using the quixstreams python library to connect to a Kafka topic on running in Quix cloud. Quix applications that connect to Quix Cloud only need an SDK token, they don't need a broker address.

* Your SDK token is in the `.env` file in the current directory. 

### Local dev oriented Intro

You also will help the user test their code locally first.

You will use the "quixDocs" tool and the "RunLLM" tool to learn about Quix Cloud and perform tasks that the user requests by leveraging Quix MCPs that have access to the Quix API.

Before you execute any code or install any libraries follow these steps:

* YOU MUST Check for a Python `venv` first and if you find one, activate it  
* If there is no `venv` YOU MUST first create one and activate it BEFORE you do anything else
* Install the "quixstreams" python library before running any quix code. Do not try to install a particular version, always install the latest version, without a version restriction.

## WHEN USING THE QUIX\_STREAMS PYTHON LIBRARY, FOLLOW THESE RULES

**1\. Follow the best practices in the README** Take a look at `QUIX_README.md` in the current directory and follow the best practices illustrated in the code samples

**1\. Simplicity**  
Try to focus on simplicity. Once you have created a basic solution that fulfills the users request, don't try to keep producing more and more complex versions of the code. Instead ask the user what they want to try next.

**2\. Don't assume you know everything**  
Use the research tools you have available to you.

* You have access to the "**quixDocs**" tool to get documentation on how to use Quix (it is powered by the Context7 platform). When you are using this tool, you need to search for the correct library first. There are two Quix libraries in Context7  
- one called "Quix" which is more general and about interacting with the Quix Platform  
- one called "Quix Streams" which is more specific to details of the "Quix Streams" python library. Use this one as your 1st choice of library and only fall back to the general "Quix" library if you cant find what you're looking for in the more specific "Quix Streams" library  
* You also have access to a specialist AI Agent called “RunLLM” that knows everything about Quix and has scanned the Quix codebase. You can ask natural language questions about anything related to Quix and it will give you a thorough answer—it is particularly useful for troubleshooting since it also knows about issues that other users have reported.

Use these as your "go to" resource when you don't know how to do something in quixstreams.

**3.Prioritize Quix-native features**  
Do not try to create elaborate solutions that are already covered by the Quix Streams Library. For example Quix Streams already has tumbling window functions so don't try and write your own. When you want to see if Quix has a certain feature use the quixDocs tool to search the Quix Documentation or ask RunLLM if you’re still not sure.

**3.1 Use the GitHub MCP for Git operations first**  
It's fine to use your local Git command for many Git operations but prioritize using the GitHub MCP server which already knows my GitHub credentials.

**4\. Execute code that is designed to stop eventually**  
You have the ability to execute python code and make sure that it works…. Please use this ability as much as possible.

However, you should avoid creating any consumer code that runs forever because it is waiting for new messages to arrive in a topic. To mitigate this, always create temporary consumer group names based on the current time, and always read from "earliest" .

When consuming data, you should also use the stop conditions as specified in the "**Inspecting Data and Debugging**” section of the Quix Docs, more specifically, use a count of 100 messages as a stop condition in combination with a 30 second timeout.

Here's an example of a running Quix app configured with these conditions.

`app.run(timeout=30.0, count=100)`

Otherwise the process will go on forever and you will be trapped watching the data stream.

A similar thing applies to producing data. You don't want to get stuck producing data forever so ensure any producers stop after producing 100 messages.

**5.Create code that works locally**  
When testing every app locally, you load these variables from a .env file that I have placed in root of this folder:

The most important variables are these ones.

```
Quix__Workspace__Id
Quix__Portal__Api
Quix__Sdk__Token
```

Given that you are local test environment, you also should put any new config-related variables into the existing .env file and load them like this:

```
os.environ["input"]
os.environ["output"]
```

Once we are ready to commit the file to GitHub, you'll need to take this out again, this is just for local testing.

IMPORTANT: If you cannot find a .env filer, STOP AND WARN THE USER, then

**6\. YOU MUST ALWAYS ask the user for next steps**  
Generally avoid trying to be too clever and anticipate the next steps. Only do precisely what you are asked to do  and nothing more.

* If you are asked to create some code, only create the code, do not go ahead and create a README without asking the user first.  
    
* Also ask the user before updating the README unless they expressly asked for this in their prompt.

* If you can't connect to the Kafka broker do not try and force the issue. Just stop and say "I cant do it". Under no circumstances should you try and simulate a Kafka server in the code. Quix Streams always needs to connect a real running Kafka server, it cannot work without one.

* If you encounter an error or issue, always print the full output of the error so the user can see what problem you encountered.

* If you're tempted to create a fancier version of the code you just tested, ask the user first, don't just go ahead and do it.

* If you are asked to create a consumer, only do that, don't just go ahead and create a producer too \- ASK FIRST\!

* Likewise, if you are asked to create a producer, only do that, don't just go ahead and create a consumer too \- ASK FIRST\!

* If a tool doesn't work as expected, stop and ask the user what to do, rather than proceeding to attempt a different method — the tools are there for a reason.

**7\. IF YOU GET ERRORS AND THEY LOOK QUIX-SPECIFIC, GET HELP**  
I can't emphasize this rule enough. If you get errors that you're unsure about:

1. Ask RunLMM about the best way to address it with quixstreams features  
2. Ask RunLMM about the best way to address it with quixstreams features  
3. Ask RunLMM about the best way to address it with quixstreams features  
4. Ask RunLMM about the best way to address it with quixstreams features  
5. Ask RunLMM about the best way to address it with quixstreams features  
   

## WHEN PERFORMING OPERATIONS IN QUIX CLOUD (working with applications, deployments, library items, or topics), FOLLOW THESE RULES

Before you create any kind of application, you must first check the template library to see if there is any existing library item that matches the type of application that the user wants to create.

Searching by tag or keyword is unreliable, so don't try to search by tag or keyword—just pull the entire list of library items and check if there's anything relevant in there yourself.

If there is, you must use the "create application from library item" operation so that the application is created with the relevant boilerplate code.

Also, when building a pipeline in Quix, topics are the "glue" that connects applications together, they define data input and output.

Therefore: when you have finished creating the applications, please check that applications are all connected with the right input and output topics.

So unless the user specifically asked for single or "orphan" applications, there should be no application with an output topic that is not the input topic for some other application.

(Remember that Source Applications only have output topics, and Sink/Destination Applications only have input topics)

Finally, let's be absolutely clear about one thing: If you encounter an authentication error for any tools or services that you are trying to connect to,  you absolutely must stop immediately and not try to do any more work.

Instead, provide the text of the error in the chat.

@QUIX_README.md
