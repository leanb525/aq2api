#!/usr/bin/env python3
"""
Amazon Q Developer CLI Simple Authentication Extractor

Extracts only: profile_arn, refresh_token, client_id, client_secret
"""

import sqlite3
import json
import os
from pathlib import Path
import platform


class AmazonQSimpleAuthExtractor:
    def __init__(self):
        self.db_paths = self._get_database_paths()

    def _get_database_paths(self) -> list:
        """Get database paths based on the operating system (returns list to check multiple locations)."""
        system = platform.system()
        paths = []

        if system == "Windows":
            data_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "amazon-q"
            paths.append(data_dir / "data.sqlite3")
        elif system == "Darwin":  # macOS
            # Primary path
            data_dir = Path.home() / "Library" / "Application Support" / "amazon-q"
            paths.append(data_dir / "data.sqlite3")

            # Additional path: /home/{user}/.aws/sso/cache (as requested)
            home_aws_path = Path("/home") / os.environ.get("USER", "") / ".aws" / "amazon-q" / "data.sqlite3"
            paths.append(home_aws_path)
        else:  # Linux and others
            data_dir = Path.home() / ".local" / "share" / "amazon-q"
            paths.append(data_dir / "data.sqlite3")

        return paths

    def extract_simple_auth(self) -> dict:
        """Extract only the requested fields: profile_arn, refresh_token, client_id, client_secret"""
        result = {
            "profile_arn": "",
            "refresh_token": "",
            "client_id": "",
            "client_secret": ""
        }

        # Try each database path until we find data
        for db_path in self.db_paths:
            if not db_path.exists():
                continue

            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # Extract profile_arn from state table
                cursor.execute("""
                    SELECT value FROM state WHERE key = ?
                """, ("api.codewhisperer.profile",))

                profile_result = cursor.fetchone()
                if profile_result:
                    profile_data = json.loads(profile_result[0])
                    result["profile_arn"] = profile_data.get("arn", "")

                # Extract refresh_token from auth_kv table
                cursor.execute("""
                    SELECT value FROM auth_kv WHERE key = ?
                """, ("codewhisperer:odic:token",))

                token_result = cursor.fetchone()
                if token_result:
                    token_data = json.loads(token_result[0])
                    result["refresh_token"] = token_data.get("refresh_token", "")

                # Extract client_id and client_secret from device registration
                cursor.execute("""
                    SELECT value FROM auth_kv WHERE key = ?
                """, ("codewhisperer:odic:device-registration",))

                cred_result = cursor.fetchone()
                if cred_result:
                    cred_data = json.loads(cred_result[0])
                    result["client_id"] = cred_data.get("client_id", "")
                    result["client_secret"] = cred_data.get("client_secret", "")

                conn.close()

                # If we found any data, return it (don't check other paths)
                if any(result.values()):
                    break

            except Exception as e:
                # Continue to next path if this one fails
                continue

        return result


def main():
    extractor = AmazonQSimpleAuthExtractor()
    auth_data = extractor.extract_simple_auth()

    # Output as compact JSON
    print(json.dumps(auth_data, separators=(',', ':')))


if __name__ == "__main__":
    main()