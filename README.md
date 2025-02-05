# KnoxDNS

KnoxDNS is a secure and privacy-focused DNS resolver that supports DNS-over-HTTPS (DoH). It aims to provide fast and encrypted DNS queries while ensuring user privacy and security.

## Features

- **DNS-over-HTTPS (DoH)**: Encrypts DNS queries for enhanced privacy.
- **High Performance**: Optimized for low latency and fast responses.
- **Security Focused**: Prevents DNS spoofing and improves user protection.
- **Customizable**: Configurable settings for different use cases.

## Installation

### Prerequisites

- Python 3.x
- pip

### Steps

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/knoxdns.git
   cd knoxdns
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the server:
   ```sh
   python main.py
   ```

## Configuration

Modify the `config.json` file to customize the DNS settings.

```json
{
  "port": 8080,
  "upstream_dns": "https://1.1.1.1/dns-query"
}
```

## Usage

### API Endpoint

Send a DNS query using DoH:

```sh
curl -X GET "http://localhost:8080/dns-query?name=example.com&type=A"
```

### Integration with System

To use KnoxDNS as your system resolver, configure your network settings to point to your KnoxDNS server.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License.

