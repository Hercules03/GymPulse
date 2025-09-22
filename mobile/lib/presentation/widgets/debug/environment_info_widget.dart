import 'package:flutter/material.dart';
import '../../../core/config/environment_config.dart';

class EnvironmentInfoWidget extends StatelessWidget {
  const EnvironmentInfoWidget({super.key});

  @override
  Widget build(BuildContext context) {
    final config = EnvironmentConfig.getConfig();
    
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Environment Configuration',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            ...config.entries.map((entry) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 120,
                    child: Text(
                      '${entry.key}:',
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      entry.value.toString(),
                      style: const TextStyle(fontFamily: 'monospace'),
                    ),
                  ),
                ],
              ),
            )),
            const SizedBox(height: 16),
            const Text(
              'Note: Update .env file to change these values',
              style: TextStyle(
                fontSize: 12,
                fontStyle: FontStyle.italic,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
