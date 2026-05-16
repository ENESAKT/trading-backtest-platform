import 'package:web_socket_channel/web_socket_channel.dart';

class WsClient {
  WebSocketChannel? _channel;

  Stream<dynamic> connectQuotes({
    required String baseUrl,
    required String symbol,
    String? token,
  }) {
    final uri = Uri.parse(baseUrl).replace(
      scheme: baseUrl.startsWith('https') ? 'wss' : 'ws',
      path: '/ws/quotes',
      queryParameters: {
        'symbol': symbol,
        if (token != null) 'token': token,
      },
    );
    _channel = WebSocketChannel.connect(uri);
    return _channel!.stream;
  }

  void close() {
    _channel?.sink.close();
  }
}
