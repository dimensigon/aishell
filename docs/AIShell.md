

[AI$\>](#ai$\>)

[Advised Tech Stack](#advised-tech-stack)

[Implementation guidelines](#implementation-guidelines)

[General Layout](#general-layout)

[Explanation of the Layout](#explanation-of-the-layout)

[Dynamic screen Allocation](#dynamic-screen-allocation)

[Modules](#modules)

[OS-Base](#os-base)

[Components (submodules)](#components-\(submodules\))

[AI-Helper](#ai-helper)

[Components (submodules)](#components-\(submodules\)-1)

[Vault / Credentials Manager](#vault-/-credentials-manager)

[Components (submodules)](#components-\(submodules\)-2)

[Database Core Module (Base Engine)](#database-core-module-\(base-engine\))

[Components (submodules)](#components-\(submodules\)-3)

[Web Interface](#web-interface)

[Components (submodules)](#components-\(submodules\)-4)

# AI$\> {#ai$>}

"AI$" (called "AI-Shell" or "AI-\<dollar\>-Shell") is a command-line interface where the user can administrate linux built in python **prompt-toolkit**. It is **multi-threaded** and it can launch multiple commands on the **background asynchronously** to enrich the panels with command-related information. It serves as an interactive shell where users can navigate the system, manage files and directories and execute any linux commands as in the regular shell.

Built in a modular manner, it can be extended with more modules to administrate other types of software running on the local system such as databases, front-end, containers and more.

On Startup, include a **matrix-like** animation where AI-Models availability is checked, with a nerdy systems check per AI Model that it is connected to the program. Finishing with a motivating random message (AI Response required from default AI model)  like "AI-$hell version X.X.X initiated. All systems **online**. How can I help you today, Operator?". This is part of the health-check, so the application is operational.

## Advised Tech Stack {#advised-tech-stack}

Unless there is a better option for the required functions, python is preferred because it has modules like "prompt-toolkit", "threading", "Flask" and modules for asynchronous I/O as well frameworks for interacting with AI Models.

"prompt-toolkit" has the functionality called "Full Screen Applications" which is preferred to be used, so multiple containers or panels can be used depending on the "module" configuration.

"Web Interface" Module would be very easy to program in Flask.

### Implementation guidelines {#implementation-guidelines}

- Build as an extensible system with modular support for different database engines  
- Implement progressive learning from user interactions  
- Create robust error handling and graceful degradation  
- Prioritize security and sensitive data protection, detecting if a command or SQL Query can provide sensitive information, in this case, a local LLM should be used.  
- Optimize for rapid response time and minimal latency, choosing between using online and self-hosted AI models for certain types of operations. As well, using a quick feedback model to perform quick analysis to determine the approach.  
- Support both novice and expert administrators, it may be good to ask the user at first startup and save this information to the configuration file.

## General Layout {#general-layout}

### Explanation of the Layout {#explanation-of-the-layout}

**"Output"** is scrollable and selectable, selected text will be copied to clipboard automatically and clipboard will have a history accessible holding control and arrow keys (Up and Down).

While selected, user can write in natural language to the AI to get information or further instructions from the AI via asynchronous call. Any prompt that does not start with a supported linux command will be treated as natural language. The program will evaluate if any launch command is within the path, if not, it will notify the user that the command has been sent to the AI for processing explaining the AI indicating the current module the user is using and the last commands for the AI to have context to help the user further.

**"Module"** is the part that informs the user with a summary of the current status of the operations related to the module. It should be just before the Prompt for the user to know for example, its current directory, server name and any other information that the module can find appropriate to the commands that the user is writting.

#### Dynamic screen Allocation {#dynamic-screen-allocation}

The percentage of screen use will depend on the current need. If the **Output** is small from the last command and the **Module** has much information to share with the user, the height will be adapted. As well, if the user is typing a multi-line command using backslashes, the **Prompt** will use more space on the screen.

"**Prompt**" is the user input part by default. If longer than the window width, word wrap multi-line is used but it will show on the left the line number, if the user uses backslashes "\\", then it will also show line numbers as necessary and the size of the prompt on the screen will adapt to fit the command. If a user has a command or a non-null, by using the shortcut "Ctrl+A" will send it to the AI asking for an explanation, impact analysis and common tips about the command.

## 

## Modules {#modules}

### OS-Base {#os-base}

Core and basic module to navigate the OS, managing files, environment variables and executing native OS commands.

#### Components (submodules) {#components-(submodules)}

- **Navigator**: It makes the OS navigation in Linux friendlier as Natural Language can be used at any time by the user by using hash ("\#" followed by a text) or typing a command that does not resolve in the path that will trigger a suggestion based on current working directory, environment variables and command history.

- **Environment Manager**: User can trigger this by entering "env" or "export" and it will open a full screen window editor ("vim" is default) where the user can edit, add or delete variables.

- **File Editor**: Similar to editing files in "vim" (default) but user can trigger the AI calls by typing "\#ai text" to generate a full file that is updated asynchronously by writing natural language. AI should output directly should contain the part of the code to be added and the line number where it should be added/replaced/removed. A suggested format would be a JSON with "type of operation", "initial line number", "final line number(optional, needed for modifications and deletions)" and "code" itself. On each AI call, the contents of the file will be sent to the AI, in case imports to the file are done from another file/s, more files will be attached if available on the filesystem.

- **Command Executor**: The main command executor that will save all executed commands to History Manager, including its exit code and number of lines returned in stdout and stderr. Uses an autocompleter from "prompt-toolkit" to help the users with built-in commands from Linux. When new binaries are added to the path, an AI Call is sent to add the typical commands to the autocomplete asynchronously so the users can autocomplete by using "tab" as usual. If a command fails, the command, together with the stderr is sent to the AI for analysis, the module bar will inform if a current analysis is on-going and the output will be shown to the user. User can select to see the real output or the explained output once the AI response has arrived by pressing a hotkey indicated at the module bar to facilitate the user. If the "Prompt" has contents and the user press the shortcut "Ctrl+A", it will send the command, together with the PATH and current directory to the AI to get some insights about what the command does and its impact on the system and expected output based on the related files that can be retrieved from the system if AI Response is declared to be agentic. Any removal operation "rm" or similar, should be sent to AI first to be analyzed, given the current directory and a list of files of the current directory or subdirs if "recursive" is given (-r/R) to inform the user which files or directories will be deleted.

- **History Manager**: An Enhanced Command History Manager. By typing "history" and a space, the user can "query" the history and navigate with the arrow keys, any selected command will replace the prompt and will allow the user to modify the command before it is executed. The history has the following format and it is displayed as a **table** including, "\#" number of commands, "Date" short date/time 24H, "$?" exit code,"\#stdout" number of lines of stdout returned, "\#stderr" number of lines of stderr returned,  "Command" if longer than the window, word wrap multi-line visualization is used. User can delete commands in History by using a "xx" shortcut (shown in "Module" bar when using History Manager), "history" command also by followed by "clear-last \<\#\>" to clean a certain number of lines of the last 

- **File Checker**: Can be used by the user or an AI-Agent to check contents of files to provide more contextual responses. It can read contents from files all around the system where the current user has access.

- **Session Spawner**: It can spawn sessions to the current user or other users if the current user is root or has privilege (in sudoers or similar) to become (sudo) another user, in order to run a command with the environment or not, depending on the option used. Similar to "sudo \-E, \--preserve-env". This can be used for the background processes, synchronous or asynchronous (2 Methods at least).

### AI-Helper {#ai-helper}

AI-Helper can execute Ad-hoc queries from user to an online AI Provider (Support for OpenAI, DeepSeek, Anthropic) or self-host solution (Support for Ollama and LocalAI). It can also behave as an Agent to have subsequent calls to other "Tools" if required. The output should return a flag to make subsequent calls (Agentic). If several AI models are configured, the user can indicate the desired model by an abbreviation in config files that the user should define and it can be used for code generation asked from "Prompt" (Ctrl+A followed by model abbreviation/keyword)  or in "File Editor" like "\#ai \<model\> \<query text\>".

#### Components (submodules) {#components-(submodules)-1}

- **Synchronous Query**: Normal to be used when the user hit "Ctrl+A" in another modules or uses "\#ai text" code generation with the "File Editor". If used from the "Prompt", it has the possibility to generate one or multiple files in the filesystem, it will show the output, the "Module" will show a way to change between the "Shell" view and the "AI Response" view with a shortcut (Ctrl \+ Arrow keys advised) and the user will have to confirm the advises changes. 

- **Asynchronous Query**: Mainly used in the background by other modules or AI to avoid impacting user input and keep the interaction efficient. It can "query" the "History Manager", "Database" Modules to execute queries if connected to any database or a "Test Database" to check dictionary tables or use any other Module or submodule in the system.

- **Failover Query**: In case a query Sync or Async has failed, a failover query can be used to another AI Model or to a self-hosted AI-Model if configured.

- **Agent**: If a call is returned with the flag to be **agentic** (tasks are described), then another subsequent call will be done to specify each call with the explicit tasks and the order to be executed by the "**Tools**".

- **Tools**: An Agentic call can use the following tools on demand, if any tool makes a addition, modification or removal of files on the system and/or changes to processes, it should present a summary of all changes to the user and ask for a written approval, depending on its given risk by the AI response, the "approve" can be accepted via a shortcut as for example "y/o" for low impact, medium impact "OK/NOK" and "Understood and approved" for high risk operations.  
  - Examples of **Tools**:  
    - "File Viewer"  
    - "File Creation"  
    - "File Modification"  
      - "Rename"  
      - "File Contents Modification"  
    - "File Deletion"  
    - "Directory Creation"  
    - "Command Execution"  
    - "Subsequent AI Call" / Sync or Asynchronous  
    - "Database: Statement Execution"  
    - "Add Secret"

### Vault / Credentials Manager {#vault-/-credentials-manager}

To save passwords, database credentials and more.

Commands can access and "prompt-toolkit" can autocomplete secrets by typing a "$vault.\<var\_name\>" in OS Shell or while writing SQL if a Database Module is used. Once the "dot" is typed, an auto-completer will help the user.

#### Components (submodules) {#components-(submodules)-2}

- **Secret Manager**:  
  Secrets should be redacted in "History Manager" or from any logging as well, from any online AI call unless the secret is sent to a self-hosted local AI Model.

  - Types:  
    - Standard, used for API\_KEYS and regular variables where a variable name and a value is stored.  
    - Database connection, a set of secrets with a pattern:  
      - username, password, host/s, port.  
    - User-defined, where a YAML schema can be provided.

### Database Core Module (Base Engine) {#database-core-module-(base-engine)}

An Abstract common framework for database engines.

#### Components (submodules) {#components-(submodules)-3}

Each Database Engine to be added, can be considered a submodule unless explicitly indicated to bypass this module.

- **Connections Manager**: Multiple connections to same or different database engines can be used. Connection Manager can show how many of these connections, status of the background sessions (AI auxiliary or long-running analysis or User-created, active, long-running or idle ones). Sessions can be reactivated to the foreground or killed on demand. A table-view is given together with information of logon time, number of statements run so far, status (active/inactive), wait class, engine used, version, commit status (if any uncommitted changes),   
- **Risk Analyzer**: Using pre-parsing and a dictionary, a dictionary of keywords together with their severity is used, if medium to high risk is determined, an AI call to determine its impact and possible improvements or suggestions are given to the user asynchronously.  Users can configure a view to change from "Output" view to "Risk view" using "Ctrl+Arrow keys".  
- **Error Handling**: Should be provided by the submodule or specific database engine.  
- **Query Output formatter**: Auto adjust dynamically the output to fit the screen for best view and make the data user friendly. It adapts to any number of columns. For example in Oracle, results can be requested in CSV mode (should be default), so this submodule can adapt the output to the current screen size to provide a table-like view.  
- **Performance Optimizer**: Should be provided by the submodule or specific database engine.  
- **NLP Processor**: Should be provided by the submodule or specific database engine.  
- **Statement Tester**: Should be provided by the submodule or specific database engine. A Test database is optional due to availability but the functionality must be provided so the users can pre-test their commands or procedural code (plus dependencies) in a test database beforehand.  
- **SQL History Manager**: Extends the "History Manager" with a new Class to store Statements executed by the user together with relevant information such as exit code, number of affected rows, number of output rows, severity, engine version, time elapsed, connection used (user name).  
- **Debugging**: Should be provided by the submodule or specific database engine. It should include at least:  
  - **Logging**: A visual way to check the main database logs (1 or more).  
  - **Tracing**: Specifying the location of the trace files, so they can be viewed from the application with the native "**Navigator**",  "**File Editor**" or "**File Viewer**".  
  - **Session Monitor**: A way to monitor user sessions, if possible, focusing on their resource utilization (workload), session waits, tracing enabling/disabling and administration (killing).

### Web Interface {#web-interface}

An on-demand web interface that can be started at any time on port 5000\. Possibility to use self-signed certificates for keeping the traffic secure and encrypted at all times.

Each module should provide a way to offer the same functionality as offered in command-line but in a graphical way.

#### Components (submodules) {#components-(submodules)-4}

- Connecting to different database engines  
- Executing queries with syntax highlighting  
- Viewing query results in a structured format  
- Analyzing and optimizing queries  
- Exporting results