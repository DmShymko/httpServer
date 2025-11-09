from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer
import os

HOST = "0.0.0.0"
PORT = 8000
UPLOAD_DIR = 'uploaded_files'

HTTP_STATUS_200_OK = 200
HTTP_STATUS_400_BAD_REQUEST = 400
HTTP_STATUS_405_NOT_ALLOWED = 405
HTTP_STATUS_500_INTERNAL_SERVER_ERROR = 500


class HttpFormFileUploadRequestHandler(BaseHTTPRequestHandler):

    def _send_response(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        content_type = self.headers.get("content-type", "")

        if not content_type.startswith("multipart/form-data"):
            self._send_response(
                HTTP_STATUS_405_NOT_ALLOWED,
                b"Method Not Allowed or Invalid Content-Type",
            )
            return

        # Handle multipart/form-data for file uploads
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)

            boundary = content_type.split("boundary=")[1].encode()
            parts = post_data.split(b"--" + boundary)

            for part in parts:
                if b"filename=" not in part:
                    continue

                headers_end_index = part.find(b"\r\n\r\n")
                if headers_end_index == -1:
                    continue

                headers = part[:headers_end_index].decode("utf-8")
                content = part[headers_end_index + 4:]

                filename_start = headers.find('filename="') + len('filename="')
                filename_end = headers.find('"', filename_start)
                filename = headers[filename_start:filename_end]

                os.makedirs(UPLOAD_DIR, exist_ok=True)
                filepath = os.path.join(UPLOAD_DIR, filename)

                with open(filepath, "wb") as f:
                    f.write(content)

                self._send_response(
                    HTTP_STATUS_200_OK,
                    f"File '{filename}' uploaded successfully.".encode(),
                )
                return

            self._send_response(
                HTTP_STATUS_400_BAD_REQUEST,
                b"No file found in the upload.",
            )

        except Exception as e:
            self._send_response(
                HTTP_STATUS_500_INTERNAL_SERVER_ERROR,
                f"Error processing upload: {e}".encode(),
            )

    def do_GET(self):
        self._send_response(
            HTTP_STATUS_200_OK,
            b"""
            <!DOCTYPE html>
            <html>
            <head><title>Upload File</title></head>
            <body>
                <h1>Upload a File</h1>
                <form action="/" method="post" enctype="multipart/form-data">
                    <input type="file" name="uploaded_file">
                    <input type="submit" value="Upload">
                </form>
            </body>
            </html>
            """,
        )


with TCPServer((HOST, PORT), HttpFormFileUploadRequestHandler) as httpd:
    print(f"Serving on http://{HOST}:{PORT}")
    print(f"Uploaded files will be saved in: {os.path.abspath(UPLOAD_DIR)}")
    httpd.serve_forever()
