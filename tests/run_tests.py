"""Main test runner script."""

import asyncio
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

from tests.integration_tests import main


if __name__ == "__main__":
    try:
        summary = asyncio.run(main())

        # Exit with non-zero if any tests failed
        if summary["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nTest runner error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)