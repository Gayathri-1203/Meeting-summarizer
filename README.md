Run main.py

Developed an Automated Meeting Assistant bot using Python to streamline meeting management.

The bot monitors unread emails for invitations, extracts and logs meeting details into a database, and joins meetings as a listener to record audio using PyAudio.

Audio is transcribed with Whisperx, generating detailed transcripts with timestamped segments. 

It utilizes the Mixtral model and a diarization model to segment conversations, identify action items, and highlight key points. 

Additionally, PaddleOCR and PyAutoGUI are employed to capture and map active speakers' names from screenshots to conversation segments. 

This solution enhances productivity by automating note-taking and action item generation, resulting in clear and organized meeting summaries.
