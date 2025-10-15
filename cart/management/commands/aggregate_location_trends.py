from django.core.management.base import BaseCommand
from datetime import date, timedelta
from django.utils import timezone
from cart.models import Order, Item, MovieLocationTrend
import json


class Command(BaseCommand):
    help = 'Aggregate order data by location to create movie location trends'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--export-json', action='store_true')
        parser.add_argument('--export-file', type=str, default='movie_trends.json')

    def handle(self, *args, **options):
        days_back = options['days']
        force_regenerate = options['force']
        export_json = options['export_json']
        export_file = options['export_file']
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        print(f'Aggregating orders from {start_date} to {end_date}')
        
        orders_with_location = Order.objects.filter(
            date__date__gte=start_date,
            date__date__lte=end_date,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        if not orders_with_location.exists():
            print('No orders with location data found')
            if export_json:
                self.export_for_google_maps(export_file)
            return
        
        print(f'Found {orders_with_location.count()} orders with location data')
        
        trends_created = 0
        trends_updated = 0
        
        location_movie_data = {}
        
        for order in orders_with_location:
            order_items = Item.objects.filter(order=order)
            
            for item in order_items:
                movie = item.movie
                city = order.city or 'Unknown'
                state = order.state or 'Unknown'
                country = order.country or 'Unknown'
                
                key = f"{movie.id}_{city}_{state}_{country}"
                
                if key not in location_movie_data:
                    location_movie_data[key] = {
                        'movie': movie,
                        'city': city,
                        'state': state,
                        'country': country,
                        'latitude': order.latitude,
                        'longitude': order.longitude,
                        'total_purchases': 0
                    }
                
                location_movie_data[key]['total_purchases'] += item.quantity
        
        # Create trends from aggregated data
        for key, data in location_movie_data.items():
            try:
                # Try to get existing trend first (any date)
                try:
                    trend = MovieLocationTrend.objects.get(
                        movie=data['movie'],
                        city=data['city'],
                        state=data['state'],
                        country=data['country']
                    )
                    # Trend exists
                    if force_regenerate:
                        trend.purchase_count += data['total_purchases']
                        trend.latitude = data['latitude']
                        trend.longitude = data['longitude']
                        trend.save()
                        trends_updated += 1
                        print(f'Updated trend: {data["movie"].name} in {data["city"]}, {data["state"]} (total: {trend.purchase_count} purchases)')
                    else:
                        print(f'Skipped existing trend: {data["movie"].name} in {data["city"]}, {data["state"]}')
                except MovieLocationTrend.DoesNotExist:
                    # Trend doesn't exist, create it
                    trend = MovieLocationTrend.objects.create(
                        movie=data['movie'],
                        city=data['city'],
                        state=data['state'],
                        country=data['country'],
                        date=end_date,
                        latitude=data['latitude'],
                        longitude=data['longitude'],
                        purchase_count=data['total_purchases']
                    )
                    trends_created += 1
                    print(f'Created trend: {data["movie"].name} in {data["city"]}, {data["state"]} ({data["total_purchases"]} purchases)')
            except Exception as e:
                print(f'Error creating trend for {data["movie"].name} in {data["city"]}, {data["state"]}: {e}')
                continue
        
        print(f'Aggregation complete - Created: {trends_created}, Updated: {trends_updated}')
        
        top_trends = MovieLocationTrend.objects.filter(
            date=end_date
        ).order_by('-purchase_count')[:10]
        
        print('Top trending movies:')
        for trend in top_trends:
            print(f'  {trend.movie.name} - {trend.city}, {trend.state} ({trend.purchase_count} purchases)')
        
        if export_json:
            self.export_for_google_maps(export_file)

    def export_for_google_maps(self, filename):
        print(f'Exporting data to {filename} for Google Maps...')
        
        trends = MovieLocationTrend.objects.all().select_related('movie')
        
        markers = []
        
        for trend in trends:
            marker = {
                'lat': float(trend.latitude),
                'lng': float(trend.longitude),
                'title': f"{trend.movie.name} - {trend.city}, {trend.state}",
                'info': f"<b>{trend.movie.name}</b><br>Location: {trend.city}, {trend.state}<br>Purchases: {trend.purchase_count}<br>Price: ${trend.movie.price}",
                'purchases': trend.purchase_count,
                'movie_name': trend.movie.name,
                'city': trend.city,
                'state': trend.state
            }
            markers.append(marker)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(markers, f, indent=2, ensure_ascii=False)
        
        print(f'Exported {len(markers)} markers to {filename}')