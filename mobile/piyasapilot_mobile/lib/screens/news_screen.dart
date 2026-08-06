/// Haberler Ekranı
///
/// Backend /api/news endpoint'inden haber listesi gösterir.
library;

import 'package:flutter/material.dart';

import '../services/api_service.dart';

class NewsScreen extends StatefulWidget {
  final ApiService api;
  const NewsScreen({super.key, required this.api});

  @override
  State<NewsScreen> createState() => _NewsScreenState();
}

class _NewsScreenState extends State<NewsScreen> {
  List<Map<String, dynamic>> _news = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await widget.api.getNews(limit: 30);
      setState(() { _news = list; _loading = false; });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401
            ? 'Haberleri görmek için giriş yapın.'
            : 'Haberler yüklenemedi (${e.statusCode})';
      });
    } catch (e) {
      setState(() { _loading = false; _error = 'Bağlantı hatası'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Haberler'),
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _load)],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.warning_amber, size: 40, color: Colors.orange),
          const SizedBox(height: 8),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _load, child: const Text('Tekrar Dene')),
        ]),
      ));
    }
    if (_news.isEmpty) {
      return const Center(
        child: Text('Haber bulunamadı.', style: TextStyle(color: Colors.grey)),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        itemCount: _news.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (ctx, i) {
          final item     = _news[i];
          final headline = item['headline'] as String? ?? '';
          final source   = item['source']   as String? ?? '';
          final pubDate  = item['published_at'] as String? ?? '';
          final isRead   = (item['is_read'] as int? ?? 0) == 1;
          final symbol   = item['symbol'] as String?;

          return ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            title: Text(
              headline,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontWeight: isRead ? FontWeight.normal : FontWeight.bold,
                fontSize: 14,
              ),
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Row(children: [
                if (symbol != null) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(symbol,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).colorScheme.onPrimaryContainer,
                      )),
                  ),
                  const SizedBox(width: 6),
                ],
                Expanded(
                  child: Text(
                    source,
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(
                  pubDate.length >= 10 ? pubDate.substring(0, 10) : pubDate,
                  style: const TextStyle(fontSize: 11, color: Colors.grey),
                ),
              ]),
            ),
          );
        },
      ),
    );
  }
}
