import 'package:flutter/material.dart';
import '../../widgets/debug/environment_info_widget.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: const SingleChildScrollView(
        child: Column(
          children: [
            EnvironmentInfoWidget(),
            Card(
              margin: EdgeInsets.all(16),
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'App Settings',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 16),
                    ListTile(
                      leading: Icon(Icons.notifications),
                      title: Text('Push Notifications'),
                      trailing: Switch(value: true, onChanged: null),
                    ),
                    ListTile(
                      leading: Icon(Icons.location_on),
                      title: Text('Location Services'),
                      trailing: Switch(value: true, onChanged: null),
                    ),
                    ListTile(
                      leading: Icon(Icons.analytics),
                      title: Text('Analytics'),
                      trailing: Switch(value: true, onChanged: null),
                    ),
                    ListTile(
                      leading: Icon(Icons.dark_mode),
                      title: Text('Dark Mode'),
                      trailing: Switch(value: false, onChanged: null),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
