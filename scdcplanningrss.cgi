#!/usr/bin/perl -w
# vim:ai:cindent:sw=4:ts=4
# https://github.com/davebiffuk/scdc-planning-rss
# Dave Holland <dave@biff.org.uk>

# 2 November 2010
# rewritten for new planning application search at
# plan.scambs.gov.uk

use strict;
use HTML::TableExtract;
use HTML::Entities qw(:DEFAULT encode_entities_numeric);
use Getopt::Std;
use CGI qw(:standard);
use LWP::UserAgent;
use WWW::Mechanize;
use DateTime;

our($opt_d, $opt_t, $opt_p, $opt_s);
my ($debug, $parish, $textoutput, $cgi, $te, $ts, $no, $loc,
		$desc, $status, $row, $rfcdate, %paid, $link);
getopts('dtp:'); # debug; text output?; parish
if($opt_d) { $debug=1; }
if($opt_t) { $textoutput=1; }
if($opt_p) { $parish=$opt_p; } else { $parish="Pampisford"; }

my $dt = DateTime->now;
my $dtm = DateTime->now;
$dtm->subtract(months=>1);

$cgi = CGI->new();
if(param()) {
	if(defined(param('parish'))) {
		$parish=param('parish');
		$parish =~ tr/a-zA-z / /cs;
	}
}

my $mech = WWW::Mechanize->new( autocheck => 1 );
$mech->get('http://plan.scambs.gov.uk/swiftlg/apas/run/wphappcriteria.display');

$mech->form_number(2);
$mech->field('APEDECDATFROM.MAINBODY.WPACIS.1', '');
$mech->field('APEDECDATTO.MAINBODY.WPACIS.1', '');
$mech->field('APELDGDATFROM.MAINBODY.WPACIS.1', '');
$mech->field('APELDGDATTO.MAINBODY.WPACIS.1', '');
$mech->field('APNID.MAINBODY.WPACIS.1', '');
$mech->field('DECFROMDATE.MAINBODY.WPACIS.1', '');
$mech->field('DECTODATE.MAINBODY.WPACIS.1', '');
$mech->field('FINALGRANTFROM.MAINBODY.WPACIS.1', '');
$mech->field('FINALGRANTTO.MAINBODY.WPACIS.1', '');
$mech->field('JUSTDEVDESC.MAINBODY.WPACIS.1', '');
$mech->field('JUSTLOCATION.MAINBODY.WPACIS.1', '');
$mech->field('SURNAME.MAINBODY.WPACIS.1', '');

#$mech->field('PARISH.MAINBODY.WPACIS.1', '1000172'); # = Pampisford
#$mech->select("PARISH.MAINBODY.WPACIS.1", $parish);
# August 2015. Gack. It's all changed, e.g. "Pampisford CP", "Milton CP (DET)"
# Let's have a match on the available parishes. Avoid "inactive"
# because of this sort of silliness:
# <option value="1000239">***Barrington (Inactive)***</option>
# <option value="1000192">***Barrington. (Inactive)***</option>
# <option value="8">***Barrington.. (Inactive)***</option>
# <option value="1000024">***Barrington.... (Inactive)***</option>

my ($parishlist) = $mech->find_all_inputs( name => 'PARISH.MAINBODY.WPACIS.1' );
my %name_lookup;
@name_lookup{ $parishlist->value_names } = $parishlist->possible_values;
foreach ($parishlist->value_names) {
	next if m/^$/;
	next if m/inactive/i;
	if (m/$parish/i) {
		$mech->select("PARISH.MAINBODY.WPACIS.1", $_);
		$debug && print "given '",$parish,"', chose '",$_,"'\n";
		last;
	}
}

$mech->field('REGFROMDATE.MAINBODY.WPACIS.1', $dtm->dmy('/') );
$mech->field('REGTODATE.MAINBODY.WPACIS.1', $dt->dmy('/') );

$mech->click('SEARCHBUTTON.MAINBODY.WPACIS.1');

my $html=$mech->content();

#$debug && print $html."\n\n";

$te = HTML::TableExtract->new( ); # there's only one table
$te->parse($html);

my $url="http://plan.scambs.gov.uk/swiftlg/apas/run/wphappcriteria.display";
$url=encode_entities($url);

if(!$textoutput) {
	print $cgi->header(-type=>"application/rss+xml");
	print <<EOT;
<?xml version="1.0"?>
<rss version='2.0' xmlns:atom='http://www.w3.org/2005/Atom'>

<channel>
<title>$parish Planning Applications (unofficial)</title>
<link>$url</link>
<description>SCDC Planning Applications for $parish (unofficial)</description>
<generator>planning-to-rss</generator>
EOT
print '<atom:link href="' . $cgi->self_url . '" rel="self" type="application/rss+xml" />', "\n";
}

chomp($rfcdate=`date --rfc-2822`);

foreach $ts ($te->tables) {
	$debug && print "Table ".$ts->coords."\n";
	foreach $row ($ts->rows) {
		($no, $desc, $loc) = @$row;
		next unless defined($no); # some blank lines...?
		next unless $no =~ m/\S+/; # and some more...?

		# trim
		$desc=~s/^\s*//;
		$desc=~s/\s*$//;
		$loc=~s/^\s*//;
		$loc=~s/\s*$//;

		if($textoutput) {
			print $no, " - ", $loc, "\n  ", $desc, "\n";
		} else {
			$loc=encode_entities($loc);
			$desc=encode_entities($desc);
			$link="http://plan.scambs.gov.uk/swiftlg/apas/run/WPHAPPDETAIL.DisplayUrl?theApnID=" . $no;
			print <<EOT;
<item>
	<title>SCDC planning application $no</title>
	<link>$link</link>
	<guid isPermaLink="false">$no</guid>
	<pubDate>$rfcdate</pubDate>
	<description>&lt;p&gt;$no - $loc&lt;/p&gt;

	&lt;p&gt;$desc&lt;/p&gt;
	</description>
	</item>
EOT
		}
	}
}

if(!$textoutput) {
	print "</channel></rss>\n";
}
