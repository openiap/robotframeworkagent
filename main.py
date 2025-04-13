import asyncio, os, traceback, json, logging
import threading
import robot
from openiap import Client

# If testing this toward app.openiap.io you MUST update the following line with your own workitem queue name
defaultwiq = "robotframeworktest"

class Worker:
    def __init__(self):
        self.client = Client()
        self.queue = None
        self.wiq = None

    def __ProcessWorkitem(self, workitem, payload):
        self.client.info(f"Processing workitem id {workitem['id']} retry #{workitem['retries']}")
        if "url" in payload:
            os.environ["url"] = payload["url"]
        result = robot.run("example.robot")
        workitem["name"] = "Robot example completed"
        if result != 0:
            raise ValueError(f"Robot example failed with exit code {result}")
        return payload

    def __ProcessWorkitemWrapper(self, workitem, initial_files):
        try:
            payload = json.loads(workitem["payload"])
            payload = self.__ProcessWorkitem(workitem, payload)
            workitem["payload"] = json.dumps(payload)
            workitem["state"] = "successful"
            
            # Get current files and determine which ones are new
            current_files = [f for f in os.listdir(".") if os.path.isfile(f)]
            new_files = [f for f in current_files if f not in initial_files]
            
            self.client.update_workitem(workitem, files=new_files)
            
            # Delete the files after sending them
            for file in new_files:
                try:
                    os.remove(file)
                except Exception as e:
                    self.client.warn(f"Failed to delete file {file}: {str(e)}")
                    
        except Exception as e:
            workitem["state"] = "retry"
            workitem["errortype"] = "application"  # Retryable error
            workitem["errormessage"] = "".join(traceback.format_exception_only(type(e), e)).strip()
            workitem["errorsource"] = "".join(traceback.format_exception(e))
            self.client.error(repr(e))
            self.client.error("".join(traceback.format_tb(e.__traceback__)))
            
            # Get current files and determine which ones are new
            current_files = [f for f in os.listdir(".") if os.path.isfile(f)]
            new_files = [f for f in current_files if f not in initial_files]
            
            self.client.update_workitem(workitem, files=new_files)
            
            # Delete the files after sending them
            for file in new_files:
                try:
                    os.remove(file)
                except Exception as e:
                    self.client.warn(f"Failed to delete file {file}: {str(e)}")

    def __loop_workitems(self):
        """Synchronous method to process work items"""
        self.client.info(f"Checking for workitems in {self.wiq} workitem queue")
        counter = 0
        
        # Get list of existing files before processing workitems
        initial_files = [f for f in os.listdir(".") if os.path.isfile(f)]
        
        while True:
            workitem = self.client.pop_workitem(self.wiq)
            if workitem is None:
                self.client.info(f"No workitems found in {self.wiq} workitem queue")
                break
            self.client.info(f"Workitem retrieved: {workitem}")
            counter += 1
            self.__ProcessWorkitemWrapper(workitem, initial_files)
        if counter > 0:
            self.client.info(f"Finished processing {counter} workitems in {self.wiq} workitem queue")
        else:
            self.client.info(f"No workitems were processed in {self.wiq} workitem queue")

    def on_connected(self):
        self.client.info("Connected to OpenIAP")
        if self.queue:
            self.client.info(f"Registering queue: {self.queue}")
            self.client.register_queue(self.queue, self.__wait_for_message)

    def __wait_for_message(self, event, count):
        self.client.info("Message received, starting workitem processing")
        # Use a simple thread to handle the processing
        thread = threading.Thread(target=self.__loop_workitems)
        thread.daemon = True
        thread.start()

    def __handle_task_exception(self, task):
        try:
            task.result()  # Retrieve the result to raise any exceptions
        except Exception as e:
            self.client.error(f"Error in task: {repr(e)}")

    async def main(self):
        self.queue = os.environ.get("queue", "")
        self.wiq = os.environ.get("wiq", "")
        if not self.wiq:
            self.wiq = defaultwiq

        self.client.enable_tracing("openiap=info")
        self.client.connect()
        self.client.on_client_event(lambda event, count: self.on_connected() if event["event"] == "SignedIn" else None)

        if not self.queue:
            self.queue = self.wiq
        if not self.queue:
            while True:
                await self.__loop_workitems()
                await asyncio.sleep(30)
        else:
            while True:
                await asyncio.sleep(1)

if __name__ == "__main__":
    loglevel = os.environ.get("loglevel", logging.INFO)
    if loglevel == logging.INFO:
        logging.basicConfig(format="%(message)s", level=loglevel)
    else:
        logging.basicConfig(format="%(levelname)s:%(message)s", level=loglevel)

    wiq = os.environ.get("wiq", "")
    if not wiq:
        wiq = defaultwiq
    if not wiq:
        raise ValueError("Workitem queue name (wiq) is required")

    worker = Worker()
    asyncio.run(worker.main())
